"""Build 384.118: Stats' Recent tests and Test history - calm rows of one height, and finding a test.
Madison, Profile > Stats: "the recent test stuff looks good, but all them stacked on top of each other is overwhelming. And when you
click test history, there should be filters, like today, this week, this month, or maybe by chapter too, or you can select which
chapters to filter by, maybe a search bar. And ensure all the boxes are the same size. And why does Hundo have a stat thing next to it?"

The fixture: 120 tests over 60 days across many units (Fire Code: chapters), the newest three a long two-unit name, a short one and a
three-unit hundo; written straight into store.testHistory after boot. Academy on an iPhone 17 Pro Max (440x956), Fire Code on an
iPad Pro 11" (834x1194). Everything is read off the page and checked against the fixture, worked out here (not by the app's own
helpers): today from 00:00, this week from Monday 00:00, this month from the 1st.
(1) Stats: at most three recent rows, all the same height, each name on one line;
(2) a hundo's marker is a chip like the mode's (same height, radius, type size) with no glyph in it - "the stat thing";
(3) Test history, nothing set: every test listed (rows are read after scrolling the whole list in), every row the same height and
    its name on one line, the count line's number = the rows, at most four date headings and the rows under one heading all on the
    same side of today / yesterday / Monday;
(4) the time switch has four segments; each of the last three lists exactly the tests since today / Monday / the 1st, the count
    line agreeing;
(5) the units button opens a sheet of checkboxes; ticking three lists exactly the tests with any of those units, and the button
    then shows a 3;
(6) the search lists exactly the tests whose unit names hold the word;
(7) the three together list exactly the intersection;
(8) a search that matches nothing lists nothing, the count says 0, and an empty state shows with a button that brings every test back;
(9) a tap on a row opens that test's page, which names its units in full; Back returns to the list;
(10) no page errors.
Run:  python3 tools/check-b384-testhistory.py   (--against REV|OLD/index.html must FAIL)"""
import os, sys, re, subprocess, tempfile, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_argv = sys.argv; sys.argv = sys.argv[:1]   # check-behaviour reads --against itself, as a path; a REV is resolved below
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
sys.argv = _argv
import b384_pop_lib as pl
if "--against" in sys.argv:
    ref = sys.argv[sys.argv.index("--against") + 1]
    if os.path.isfile(ref):
        body = open(ref, encoding="utf-8").read()
    else:
        body = subprocess.run(["git", "-C", os.path.dirname(HERE), "show", ref + ":index.html"], capture_output=True, text=True, check=True).stdout
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright

ok = True
def chk(name, cond, info=""):
    global ok
    ok = ok and bool(cond)
    print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)


def boot(br, cls, w, h):
    ctx = br.new_context(viewport={"width": w, "height": h}, has_touch=True, is_mobile=True, device_scale_factor=2)
    ctx.set_default_navigation_timeout(180000); ctx.set_default_timeout(180000)
    if cls == "ifc":
        ctx.add_init_script("try{localStorage.setItem('class26e.activeclass','ifc');" + pl.SEEN_IFC + "}catch(e){}")
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                        "localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');"
                        "localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');"
                        "localStorage.setItem('class26e.drill.v1', '%s');}catch(e){}" % pl.BOTH)
    pg = cb.open_page(ctx)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(cb.URL, timeout=180000)
    pg.wait_for_timeout(3000)
    pg.evaluate("()=>{ try{ store.savedCodeSaved = true; localStorage.setItem('class26e.savecode.card','1'); }catch(e){} }")
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); __stub(); try{ homeUnlocksOwed = () => false; }catch(e){} }")
    return ctx, pg, errs


# 120 tests over 60 days; deterministic. The newest three: two long unit names together, the shortest name, a three-unit hundo.
FIXTURE = r"""(o) => {
  const units = (typeof unitsInTeachingOrder === 'function' ? unitsInTeachingOrder() : topicsIn(QUESTIONS)).filter(Boolean);
  const title = u => (typeof unitTitle === 'function' ? unitTitle(u) : u);
  const N = 120, DAYS = 60, now = Date.now();
  let s = 4242; const rnd = () => (s = (s * 48271) % 2147483647) / 2147483647;
  const modes = o.ifc ? ['drill', 'drill', 'drill', 'game'] : ['drill', 'drill', 'exam', 'exam', 'game'];
  const pool = units.slice(0, Math.min(units.length, 20));
  const byLen = pool.slice().sort((a, b) => title(b).length - title(a).length);
  const out = [];
  for(let i = 0; i < N; i++){
    const d0 = new Date(now), yNoon = new Date(d0.getFullYear(), d0.getMonth(), d0.getDate() - 1, 12).getTime();
    const t = i < 3 ? now - (i + 1) * 60000 : i === 3 ? yNoon : now - Math.round((i / N) * DAYS * 86400000) - Math.round(rnd() * 3600000);
    let us;
    if(i === 0) us = [byLen[0], byLen[1]];
    else if(i === 1) us = [byLen[byLen.length - 1]];
    else if(i === 2) us = [pool[0], pool[1], pool[2]];
    else { const k = rnd() < .15 ? 2 + Math.floor(rnd() * 2) : 1; us = []; for(let j = 0; j < 9 && us.length < k; j++){ const u = pool[Math.floor(rnd() * pool.length)]; if(!us.includes(u)) us.push(u); } }
    const n = 10 + Math.floor(rnd() * 20);
    let good = Math.max(0, n - Math.floor(rnd() * 9));
    if(i === 2 || i % 9 === 4) good = n;
    const pct = Math.round(good / n * 100);
    const e = { label: us.join(', '), units: us, pct, n, ok: good, elapsedMs: 60000 + Math.round(rnd() * 600000), playedAt: t, mode: modes[Math.floor(rnd() * modes.length)] };
    if(pct === 100) e.hundos = us.length;
    if(i > 2 && rnd() < .08){ e.vr = true; e.mode = 'drill'; }
    out.push(e);
  }
  store.testHistory = out;
  return { n: out.length, units: [...new Set(out.flatMap(e => e.units))].length };
}"""

# Independent of the app: the day starts, an entry's searchable words, the expected list for a set of filters.
EXPECT = r"""(f) => {
  const d = new Date(), y = d.getFullYear(), m = d.getMonth(), day = d.getDate();
  const today = new Date(y, m, day).getTime(), yest = new Date(y, m, day - 1).getTime();
  const week = new Date(y, m, day - ((d.getDay() + 6) % 7)).getTime(), month = new Date(y, m, 1).getTime();
  const from = { all: null, today, week, month }[f.when || 'all'];
  const title = u => (typeof unitTitle === 'function' ? unitTitle(u) : u);
  const units = f.units && f.units.length ? new Set(f.units) : null;
  const q = String(f.q || '').toLowerCase();
  const list = (store.testHistory || []).filter(e => {
    if(from != null && !(e.playedAt >= from)) return false;
    if(units && !e.units.some(u => units.has(u))) return false;
    if(q && !e.units.map(title).join(' ').toLowerCase().includes(q)) return false;
    return true;
  });
  return { ats: list.map(e => String(e.playedAt)), bounds: { today, yest, week, month } };
}"""

# Every row of the list on the page, after scrolling it all in (a long list may be put on the page in parts).
READ = r"""async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const scr = document.querySelector('#stage .screen-testhistory');
  if(!scr) return null;
  let n = -1;
  for(let i = 0; i < 40; i++){
    const rows = scr.querySelectorAll('.thx-row');
    if(rows.length === n) break;
    n = rows.length;
    window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' });
    await wait(260);
  }
  const rows = [...scr.querySelectorAll('.thx-row')];
  const lh = el => { const c = getComputedStyle(el); return parseFloat(c.lineHeight) || parseFloat(c.fontSize) * 1.3; };
  const cl = scr.querySelector('.thx-count');
  const heads = [...scr.querySelectorAll('.thx-day')].map(h => ({ ats: [] , el: h }));
  const out = {
    ats: rows.map(r => r.dataset.at || null),
    heights: rows.map(r => Math.round(r.getBoundingClientRect().height * 10) / 10),
    multiLine: rows.filter(r => { const nm = r.querySelector('.thx-row-name'); return nm && nm.getBoundingClientRect().height > lh(nm) * 1.5; }).length,
    count: cl ? ((cl.textContent.match(/\d+/) || [null])[0]) : null,
    countShown: !!(cl && cl.getClientRects().length),
    headings: [], overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth
  };
  /* the rows under each heading, by data-at */
  let cur = null;
  scr.querySelectorAll('.thx-day, .thx-row').forEach(el => {
    if(el.classList.contains('thx-day')){ cur = { rows: [] }; out.headings.push(cur); }
    else if(cur) cur.rows.push(el.dataset.at || null);
  });
  window.scrollTo({ top: 0, behavior: 'instant' });
  return out;
}"""

CHIPS = r"""(sel) => {
  const rows = [...document.querySelectorAll(sel)];
  const res = [];
  rows.forEach(r => {
    const meta = r.querySelector('.thx-row-meta'); if(!meta) return;
    const kids = [...meta.children];
    const mode = kids[0];
    kids.slice(1).filter(k => !k.classList.contains('thx-row-bit')).forEach(k => {
      const a = getComputedStyle(mode), b = getComputedStyle(k), ra = mode.getBoundingClientRect(), rb = k.getBoundingClientRect();
      res.push({ text: k.textContent, glyph: k.querySelectorAll('svg, img').length + (/[✦★☆✨]/.test(k.textContent) ? 1 : 0),
                 dh: Math.abs(ra.height - rb.height), radius: [a.borderTopLeftRadius, b.borderTopLeftRadius], fs: [a.fontSize, b.fontSize],
                 pad: [a.paddingLeft, b.paddingLeft], border: [a.borderTopWidth, b.borderTopWidth], dy: Math.abs((ra.top + ra.bottom) / 2 - (rb.top + rb.bottom) / 2) });
    });
  });
  return res;
}"""


def same(xs, tol=0.6):
    return bool(xs) and max(xs) - min(xs) <= tol


def run(br, cls, w, h, label):
    tag = "%s %s" % (label, cls)
    ctx, pg, errs = boot(br, cls, w, h)
    fx = pg.evaluate(FIXTURE, {"ifc": cls == "ifc"})
    print("  fixture:", fx, flush=True)
    N = fx["n"]
    # (1) Stats
    pg.evaluate("()=>showProfile('stats')"); pg.wait_for_timeout(1600)
    st = pg.evaluate(r"""()=>{ const sect = document.querySelector('#stage .profile-stats-tab .stx-recent'); if(!sect) return null;
      const rows = [...sect.querySelectorAll('.thx-row')];
      const lh = el => { const c = getComputedStyle(el); return parseFloat(c.lineHeight) || parseFloat(c.fontSize) * 1.3; };
      return { n: rows.length, heights: rows.map(r => Math.round(r.getBoundingClientRect().height * 10) / 10),
               multi: rows.filter(r => { const nm = r.querySelector('.thx-row-name'); return nm && nm.getBoundingClientRect().height > lh(nm) * 1.5; }).length }; }""")
    chk("(1) %s Stats: at most 3 recent rows, every one the same height, each name on one line (%s)" % (tag, st),
        st and 1 <= st["n"] <= 3 and same(st["heights"]) and st["multi"] == 0, st)
    ch = pg.evaluate(CHIPS, "#stage .profile-stats-tab .stx-recent .thx-row")
    bad = [c for c in ch if c["glyph"] or c["dh"] > 1 or c["dy"] > 1.5 or c["radius"][0] != c["radius"][1] or c["fs"][0] != c["fs"][1] or c["pad"][0] != c["pad"][1] or c["border"][0] != c["border"][1]]
    chk("(2) %s Stats: a hundo's marker is a chip like the mode's, no glyph (%d markers)" % (tag, len(ch)), ch and not bad, bad[:2] or ch)
    # into Test history by its own entry under the rows
    pg.evaluate(r"""()=>{ const sect = document.querySelector('#stage .profile-stats-tab .stx-recent');
      const btns = [...sect.querySelectorAll('button')].filter(b => !b.closest('.thx-list') && !b.classList.contains('thx-row')); btns[btns.length - 1].click(); }""")
    pg.wait_for_timeout(1500)
    allx = pg.evaluate(EXPECT, {})
    b = allx["bounds"]
    def bucket(at):
        t = int(at)
        return 0 if t >= b["today"] else 1 if t >= b["yest"] else 2 if t >= b["week"] else 3
    r0 = pg.evaluate(READ)
    if not r0:
        chk("(3) %s Test history opens from Stats" % tag, False, "no .screen-testhistory")
        ctx.close(); return
    chk("(3) %s nothing set: all %d tests listed, one height, names on one line, no sideways scroll (%d rows, heights %s, %d multi-line)"
        % (tag, N, len(r0["ats"]), sorted(set(r0["heights"])), r0["multiLine"]),
        len(r0["ats"]) == N and set(r0["ats"]) == set(allx["ats"]) and same(r0["heights"]) and r0["multiLine"] == 0 and r0["overflowX"] <= 0,
        {k: r0[k] for k in ("heights", "multiLine", "overflowX")})
    chk("(3) %s the count line says %s" % (tag, r0["count"]), r0["countShown"] and r0["count"] is not None and int(r0["count"]) == N, r0["count"])
    hb = [sorted(set(bucket(a) for a in hd["rows"] if a)) for hd in r0["headings"]]
    chk("(3) %s at most four date headings, each holding one day bucket (today / yesterday / this week / earlier) %s" % (tag, hb),
        1 <= len(r0["headings"]) <= 4 and all(len(x) == 1 for x in hb) and [x[0] for x in hb] == sorted(x[0] for x in hb), hb)
    allh = list(r0["heights"])
    # (4) the time switch
    segs = pg.evaluate("()=>[...document.querySelectorAll('#stage .screen-testhistory .navsegment > .iconbtn')].length")
    chk("(4) %s a time switch of four segments (%s)" % (tag, segs), segs == 4, segs)
    for i, when in ((1, "today"), (2, "week"), (3, "month")):
        if segs != 4:
            chk("(4) %s %s" % (tag, when), False, "no switch"); continue
        pg.evaluate("(i)=>document.querySelectorAll('#stage .screen-testhistory .navsegment > .iconbtn')[i].click()", i); pg.wait_for_timeout(700)
        r = pg.evaluate(READ); ex = pg.evaluate(EXPECT, {"when": when})
        allh += r["heights"]
        chk("(4) %s segment %d lists exactly the tests since %s (%d of %d; expected %d), the count %s" % (tag, i, when, len(r["ats"]), N, len(ex["ats"]), r["count"]),
            set(r["ats"]) == set(ex["ats"]) and len(r["ats"]) == len(ex["ats"]) and len(ex["ats"]) < N and r["count"] is not None and int(r["count"]) == len(ex["ats"]),
            {"got": len(r["ats"]), "want": len(ex["ats"]), "count": r["count"]})
    if segs == 4:
        pg.evaluate("()=>document.querySelectorAll('#stage .screen-testhistory .navsegment > .iconbtn')[0].click()"); pg.wait_for_timeout(600)
    # (5) the units sheet
    has_btn = pg.evaluate("()=>!!document.querySelector('#stage .screen-testhistory .thx-units-btn')")
    picked = []
    if has_btn:
        pg.evaluate("()=>document.querySelector('#stage .screen-testhistory .thx-units-btn').click()"); pg.wait_for_timeout(900)
        vals = pg.evaluate("()=>[...document.querySelectorAll('.invite-overlay input[type=checkbox]')].map(c=>c.value)")
        picked = vals[1:6:2] if len(vals) >= 6 else vals[:3]
        pg.evaluate("(v)=>[...document.querySelectorAll('.invite-overlay input[type=checkbox]')].filter(c=>v.includes(c.value)).forEach(c=>c.click())", picked)
        pg.wait_for_timeout(700)
        pg.evaluate("()=>{ const d=document.querySelector('.invite-overlay .thx-pick-done'); if(d) d.click(); else document.querySelector('.invite-overlay').click(); }")
        pg.wait_for_timeout(700)
        r = pg.evaluate(READ); ex = pg.evaluate(EXPECT, {"units": picked})
        allh += r["heights"]
        btxt = pg.evaluate("()=>document.querySelector('#stage .screen-testhistory .thx-units-btn').textContent")
        chk("(5) %s three units ticked in the sheet (of %d) list exactly their tests (%d; expected %d), the count %s, the button shows 3 (%r)"
            % (tag, len(vals), len(r["ats"]), len(ex["ats"]), r["count"], btxt),
            len(picked) == 3 and set(r["ats"]) == set(ex["ats"]) and 0 < len(ex["ats"]) < N and r["count"] is not None and int(r["count"]) == len(ex["ats"])
            and re.findall(r"\d+", btxt or "") == ["3"], {"got": len(r["ats"]), "want": len(ex["ats"])})
        # clear the units again through the sheet's own Clear
        pg.evaluate("()=>document.querySelector('#stage .screen-testhistory .thx-units-btn').click()"); pg.wait_for_timeout(800)
        pg.evaluate("()=>{ const c=document.querySelector('.invite-overlay .thx-pick-none'); c && c.click(); const d=document.querySelector('.invite-overlay .thx-pick-done'); d && d.click(); }")
        pg.wait_for_timeout(700)
        rc = pg.evaluate(READ)
        chk("(5) %s the sheet's Clear lists every test again (%d)" % (tag, len(rc["ats"])), len(rc["ats"]) == N, len(rc["ats"]))
    else:
        chk("(5) %s a units button that opens a sheet" % tag, False, "none")
    # (6) the search: the longest word of a unit's name that some tests have and some do not
    word = pg.evaluate(r"""()=>{ const title = u => (typeof unitTitle === 'function' ? unitTitle(u) : u);
      const H = store.testHistory, us = [...new Set(H.flatMap(e => e.units))];
      for(const u of us){ const w = title(u).toLowerCase().split(/[^a-z]+/).filter(x => x.length >= 6).sort((a, b) => b.length - a.length)[0];
        if(!w) continue; const n = H.filter(e => e.units.map(title).join(' ').toLowerCase().includes(w)).length;
        if(n >= 3 && n <= H.length / 3 && !/drill|mock|game|virtual|room|hundo/.test(w)) return w; } return null; }""")
    sinp = pg.evaluate("()=>!!document.querySelector('#stage .screen-testhistory input[type=search], #stage .screen-testhistory input.searchbox')")
    def typeq(q):
        pg.evaluate("(q)=>{ const s=document.querySelector('#stage .screen-testhistory input[type=search], #stage .screen-testhistory input.searchbox'); s.value=q; s.dispatchEvent(new Event('input',{bubbles:true})); }", q)
        pg.wait_for_timeout(700)
    if sinp and word:
        typeq(word)
        r = pg.evaluate(READ); ex = pg.evaluate(EXPECT, {"q": word})
        allh += r["heights"]
        chk("(6) %s the search %r lists exactly the tests whose units hold it (%d; expected %d), the count %s" % (tag, word, len(r["ats"]), len(ex["ats"]), r["count"]),
            set(r["ats"]) == set(ex["ats"]) and 0 < len(ex["ats"]) < N and r["count"] is not None and int(r["count"]) == len(ex["ats"]), {"got": len(r["ats"]), "want": len(ex["ats"])})
    else:
        chk("(6) %s a search field (word %r)" % (tag, word), False, "none")
    # (7) all three together: this month, three units, the search word
    if segs == 4 and has_btn and sinp and word:
        combo = pg.evaluate(r"""(w)=>{ const title = u => (typeof unitTitle === 'function' ? unitTitle(u) : u);
          const d = new Date(), month = new Date(d.getFullYear(), d.getMonth(), 1).getTime();
          const H = store.testHistory.filter(e => e.playedAt >= month);
          const hit = H.filter(e => e.units.map(title).join(' ').toLowerCase().includes(w));
          const us = [...new Set(hit.flatMap(e => e.units))].slice(0, 1);
          const more = [...new Set(H.flatMap(e => e.units))].filter(u => !us.includes(u)).slice(0, 2);
          return us.concat(more); }""", word)
        pg.evaluate("()=>document.querySelectorAll('#stage .screen-testhistory .navsegment > .iconbtn')[3].click()"); pg.wait_for_timeout(600)
        pg.evaluate("()=>document.querySelector('#stage .screen-testhistory .thx-units-btn').click()"); pg.wait_for_timeout(800)
        pg.evaluate("(v)=>[...document.querySelectorAll('.invite-overlay input[type=checkbox]')].filter(c=>v.includes(c.value)).forEach(c=>c.click())", combo)
        pg.wait_for_timeout(500)
        pg.evaluate("()=>{ const d=document.querySelector('.invite-overlay .thx-pick-done'); if(d) d.click(); else document.querySelector('.invite-overlay').click(); }")
        pg.wait_for_timeout(700)
        r = pg.evaluate(READ); ex = pg.evaluate(EXPECT, {"when": "month", "units": combo, "q": word})
        exu = pg.evaluate(EXPECT, {"when": "month", "units": combo})
        allh += r["heights"]
        chk("(7) %s this month + %d units + %r together list exactly the intersection (%d; expected %d; month and units alone %d), the count %s"
            % (tag, len(combo), word, len(r["ats"]), len(ex["ats"]), len(exu["ats"]), r["count"]),
            set(r["ats"]) == set(ex["ats"]) and len(ex["ats"]) >= 1 and r["count"] is not None and int(r["count"]) == len(ex["ats"]), {"got": len(r["ats"]), "want": len(ex["ats"])})
    else:
        chk("(7) %s the filters combine" % tag, False, "a filter is missing")
    # (8) nothing matches
    if sinp:
        typeq("zzqxv")
        r = pg.evaluate(READ)
        em = pg.evaluate(r"""()=>{ const scr = document.querySelector('#stage .screen-testhistory');
          const e = [...scr.querySelectorAll('div, section, p')].find(x => x.querySelector('button') && !x.querySelector('.thx-row') && !x.closest('.thx-tools, .thx-countrow, .searchwrap, .navsegment, .ios-navbar') && x.getClientRects().length
            && x.getBoundingClientRect().top > (scr.querySelector('.thx-count') || scr).getBoundingClientRect().bottom - 1);
          return e ? { cls: e.className, h: Math.round(e.getBoundingClientRect().height), btn: !!e.querySelector('button') } : null; }""")
        chk("(8) %s a search matching nothing: no rows, the count 0, an empty state with a button (%s, count %s)" % (tag, em, r["count"]),
            len(r["ats"]) == 0 and r["count"] == "0" and em and em["h"] >= 60, {"rows": len(r["ats"]), "count": r["count"], "empty": em})
        if em:
            pg.evaluate("(c)=>{ const scr=document.querySelector('#stage .screen-testhistory'); const e=[...scr.querySelectorAll('div')].find(x=>x.className===c); e && e.querySelector('button').click(); }", em["cls"])
            pg.wait_for_timeout(800)
            r = pg.evaluate(READ)
            allh += r["heights"]
            chk("(8) %s its button brings every test back (%d, count %s)" % (tag, len(r["ats"]), r["count"]), len(r["ats"]) == N and r["count"] is not None and int(r["count"]) == N, len(r["ats"]))
    chk("(3) %s every row in every list above is the same height (%s)" % (tag, sorted(set(allh))), same(allh), sorted(set(allh)))
    # (9) a tap opens the test
    tgt = pg.evaluate(r"""()=>{ const rows = [...document.querySelectorAll('#stage .screen-testhistory .thx-row')]; const r = rows[0]; if(!r) return null;
      const e = store.testHistory.find(x => String(x.playedAt) === r.dataset.at) || store.testHistory[0];
      return { at: r.dataset.at || null, names: e.units.map(u => (typeof unitTitle === 'function' ? unitTitle(u) : u)) }; }""")
    pg.evaluate("()=>document.querySelectorAll('#stage .screen-testhistory .thx-row')[0].click()"); pg.wait_for_timeout(1200)
    det = pg.evaluate("()=>{ const d=document.querySelector('#stage .screen-testdetail'); return d ? d.innerText : null; }")
    chk("(9) %s a tap on a row opens its test, which names its units in full (%s)" % (tag, tgt and tgt["names"]),
        det is not None and tgt and tgt["at"] and all(n in det for n in tgt["names"]), {"row data-at": tgt and tgt["at"], "page": (det or "")[:160].replace("\n", " | ")})
    pg.evaluate("()=>{ const b=document.querySelector('#stage .screen-testdetail .back-link, #stage .screen-testdetail button'); b && b.click(); }"); pg.wait_for_timeout(1200)
    back = pg.evaluate("()=>!!document.querySelector('#stage .screen-testhistory')")
    chk("(9) %s Back returns to the list" % tag, back, back)
    chk("(10) %s no page errors" % tag, not errs, errs[:2])
    ctx.close()


with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=cb.CHROME)
    try:
        run(br, "academy", 440, 956, "iPhone 17 Pro Max")
        run(br, "ifc", 834, 1194, "iPad Pro 11\"")
    finally:
        br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
