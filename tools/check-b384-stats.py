"""Build 384: Stats and Profile, from Madison's notes.
"The back to top button, that button needs to match the look of the bottom tab" / "the big thing at the top of at a glance with
the accuracy circle ... It's gonna be red for most people because questions are hard ... I love the circle and red ... i just don't
like what it's tracking. Is there something instead of accuracy it could track there" / "The box with the 4 stats, maybe it should
have the lines in the box similar to the settings ... maybe the same thing could be done for numbers in study time" / "The test
history button, not a fan ... a bigger button under the last test shown there under recent test" / "In profile, the customize
button, the badge button, and rank button. I actually do not like that at all. It's terrible. Please change that".
iPhone 17 Pro Max (440x956), dark; the iPad Pro 11" (834x1194) where it says so. All numbers are read off the page:
(1) Back to top, shown: the tab bar's glass - its fill, its rim, its blur and its shadow, computed, equal;
(2) the ring at the top of Stats reads the question bank, not accuracy: seeded with 40% of this class's questions answered right
    at least once (n > m) and an accuracy of 92%, it shows floor(right / bank) and its colour is the pass rule's red (under 70);
    a right answer on a question never answered right fills it by one question, and a miss on a known question takes nothing;
    at 75% of the bank it is green;
(3) hairlines in both four-number boxes (At a glance, Study time): on a phone a cross - an upright in the column gap's middle on
    each row and one line across the row gap from the grid's left edge to its right - white at 8%+, 1px; on the iPad, one row
    of four with an upright between each pair and no line across;
(4) Test history: nothing in Recent tests' heading; a row under the last test, the tests' width, 56px+, its tile, its name at
    18px+ - and a tap opens the history;
(5) Profile's Customize, Badge case and Rank ladder are rows: each a dark glass (fill luminance under .1, a light rim), a 32px+
    tile, its name at 18px+ and a chevron; the case's row within 10px of Customize's width; each still opens its screen;
(6) no page errors.
Run:  python3 tools/check-b384-stats.py   (--against OLD/index.html must FAIL)"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b384st"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
def nums(s): return [float(x) for x in re.findall(r"[\d.]+", s or "")]
def rgb(s):
    s = (s or "").strip()
    if s.startswith("#") and len(s) in (4, 7):
        h = s[1:] if len(s) == 7 else "".join(c * 2 for c in s[1:])
        return [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    v = nums(s)[:4]
    if (s or "").startswith("color("): v = [x * 255 for x in v[:3]] + v[3:]
    return v
def lum(v):
    f = lambda u: (u / 255 / 12.92) if u / 255 <= .03928 else ((u / 255 + .055) / 1.055) ** 2.4
    return .2126 * f(v[0]) + .7152 * f(v[1]) + .0722 * f(v[2])
SEED = """(frac)=>{ const keys=[...new Set(KEYS)]; store.stats={}; const n=Math.round(keys.length*frac);
  keys.forEach((k,i)=>{ if(i<n) store.stats[k]={ n:3, m:1, r:[] }; else if(i<n+20) store.stats[k]={ n:2, m:2, r:[] }; });
  store.lifetime.answered=5000; store.lifetime.correct=4600; saveStore(); return { right:n, bank:keys.length, firstMissed: KEYS.indexOf(keys[n]), firstKnown: KEYS.indexOf(keys[0]) }; }"""
RING = """()=>{ const r=document.querySelector('#stage .profile-stats-tab .stx-glance .thx-ring'); if(!r) return null;
  return { text: (r.querySelector('.thx-ring-num')||{}).textContent, tone: getComputedStyle(r).getPropertyValue('--tone').trim() }; }"""
LINES = """()=>{ const out=[]; document.querySelectorAll('#stage .profile-stats-tab .stat-grid-four').forEach(gr=>{ const cards=[...gr.querySelectorAll(':scope > button.stat-card')];
  const gb=gr.getBoundingClientRect();
  const segs=[]; cards.forEach((c,i)=>{ const cr=c.getBoundingClientRect(); for(const pe of ['::before','::after']){ const s=getComputedStyle(c,pe); if(s.content==='none' || s.display==='none') continue;
      const w=parseFloat(s.width), h=parseFloat(s.height); const l=parseFloat(s.left), t=parseFloat(s.top);
      const x = cr.left + c.clientLeft + l, y = cr.top + c.clientTop + t;
      segs.push({ card:i, x:Math.round(x*2)/2, y:Math.round(y*2)/2, w:Math.round(w*2)/2, h:Math.round(h*2)/2, bg:s.backgroundColor }); } });
  out.push({ cols: getComputedStyle(gr).gridTemplateColumns.split(' ').length, gap: parseFloat(getComputedStyle(gr).columnGap), gl: gb.left, gr: gb.right,
             cards: cards.map(c=>{ const r=c.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }), segs }); }); return out; }"""
def judge_lines(grids, phone):
    bad = []
    if len(grids) < 2: return ["%d four-number boxes" % len(grids)]
    for gi, gd in enumerate(grids):
        segs = gd["segs"]
        up = [s for s in segs if s["w"] <= 1.5 and s["h"] >= 30]
        across = [s for s in segs if s["h"] <= 1.5 and s["w"] >= 30]
        okc = all(len(rgb(s["bg"])) > 3 and rgb(s["bg"])[3] >= .08 and min(rgb(s["bg"])[:3]) >= 200 for s in up + across)
        cards = gd["cards"]
        if phone:
            # an upright in each row, in the column gap's middle; across: from the grid's left to its right
            mid = (cards[0][2] + cards[1][0]) / 2
            rows_up = sorted(set(round(s["y"]) for s in up))
            xs_ok = all(abs((s["x"] + s["w"] / 2) - mid) <= 1.5 for s in up)
            span = (min(s["x"] for s in across), max(s["x"] + s["w"] for s in across)) if across else (0, 0)
            gapmid = (cards[0][3] + cards[2][1]) / 2
            ok = gd["cols"] == 2 and len(up) == 2 and len(rows_up) == 2 and xs_ok and across and abs(span[0] - gd["gl"]) <= 1.5 and abs(span[1] - gd["gr"]) <= 1.5 \
                 and all(abs(s["y"] - gapmid) <= 1.5 for s in across) and okc
        else:
            ok = gd["cols"] == 4 and len(up) == 3 and not across and okc
        if not ok: bad.append((gi, gd["cols"], len(up), len(across), [s for s in segs][:5]))
    return bad
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    st = g["store"](testHistory=[{ "label": "Unit", "units": ["Unit"], "pct": 90 - i, "elapsedMs": 300000, "playedAt": 1790000000000 - i * 3600000, "mode": "drill", "n": 10, "ok": 9 } for i in range(5)])
    ctx, pg = g["open_page"](br, g["init_account"]("", st), errs=errs)
    # (1) back to top
    pg.evaluate("()=>{ showProfile('stats'); }"); pg.wait_for_timeout(1100)
    pg.evaluate("()=>{ window.scrollTo(0, document.documentElement.scrollHeight); window.dispatchEvent(new Event('scroll')); }"); pg.wait_for_timeout(1100)
    look = pg.evaluate("""()=>{ const P=['backgroundColor','backgroundImage','borderTopColor','borderTopWidth','backdropFilter','boxShadow']; const o={};
      for(const [k,s] of [['tabs','.bottomtabs'],['btt','#backtotop']]){ const e=document.querySelector(s); const c=getComputedStyle(e); o[k]=Object.fromEntries(P.map(p=>[p,c[p]])); o[k].shown = e.classList.contains('show'); } return o; }""")
    same = all(look["tabs"][p] == look["btt"][p] for p in look["tabs"] if p != "shown")
    ck("(1) Back to top (shown: %s) wears the tab bar's glass: fill %s / %s, blur %s / %s" % (look["btt"]["shown"], look["btt"]["backgroundColor"], look["tabs"]["backgroundColor"], look["btt"]["backdropFilter"], look["tabs"]["backdropFilter"]),
       look["btt"]["shown"] and same, look)
    # (2) the ring
    sd = pg.evaluate(SEED, .4)
    pg.evaluate("()=>{ showHome(); showProfile('stats'); window.scrollTo(0,0); }"); pg.wait_for_timeout(1100)
    r1 = pg.evaluate(RING)
    want = sd["right"] * 100 // sd["bank"]
    tone1 = rgb(r1 and r1["tone"])
    red = tone1 and tone1[0] > 200 and tone1[1] < 150
    pg.evaluate("(i)=>{ recordResult(i, false); saveStore(); }", sd["firstMissed"])
    pg.evaluate("(i)=>{ recordResult(i, true); saveStore(); }", sd["firstKnown"])
    after = pg.evaluate("()=>{ const keys=[...new Set(KEYS)]; return keys.filter(k=>{ const s=store.stats[k]; return s && s.n > s.m; }).length; }")
    pg.evaluate("()=>{ showHome(); showProfile('stats'); }"); pg.wait_for_timeout(1000)
    r2 = pg.evaluate(RING)
    pg.evaluate(SEED, .75); pg.evaluate("()=>{ showHome(); showProfile('stats'); }"); pg.wait_for_timeout(1000)
    r3 = pg.evaluate(RING); tone3 = rgb(r3 and r3["tone"])
    green = tone3 and tone3[1] > 180 and tone3[0] < 150
    ck("(2) the ring reads the bank (%s of %s right -> %s%%, not accuracy 92%%): %s, red %s; one more learned, one known missed -> %s right, ring %s; 75%% -> %s green %s"
       % (sd["right"], sd["bank"], want, r1, red, after, r2, r3, green),
       r1 and r1["text"] == "%d%%" % want and red and after == sd["right"] + 1 and r2 and r2["text"] == "%d%%" % ((sd["right"] + 1) * 100 // sd["bank"])
       and r3 and r3["text"] == "%d%%" % (int(sd["bank"] * .75 + .5) * 100 // sd["bank"]) and green, [sd, r1, r2, r3])
    # (3) hairlines, phone
    g1 = pg.evaluate(LINES); bad1 = judge_lines(g1, True)
    ck("(3) phone: a cross of hairlines in both four-number boxes", not bad1, bad1[:2])
    # (4) Test history
    th = pg.evaluate("""()=>{ const sect=document.querySelector('#stage .profile-stats-tab .stx-recent'); if(!sect) return null;
      const top=sect.querySelector('.stx-recent-top'); const rows=[...sect.querySelectorAll('.thx-list > *')]; const last=rows[rows.length-1];
      const btns=[...sect.querySelectorAll('button')].filter(b=>!b.closest('.thx-list'));
      const b=btns[btns.length-1]; if(!b || !last) return { headBtn: top ? top.querySelectorAll('button').length : 0, rows: rows.length };
      const br=b.getBoundingClientRect(), lr=last.getBoundingClientRect(); const tile=b.querySelector('.settings-row-icon'); const lab=b.querySelector('.pf-act-label') || b;
      return { headBtn: top ? top.querySelectorAll('button').length : 0, below: br.top >= lr.bottom - 1, wDiff: Math.abs(br.width - lr.width), lDiff: Math.abs(br.left - lr.left), h: br.height,
               tile: tile ? tile.getBoundingClientRect().width : 0, label: parseFloat(getComputedStyle(lab).fontSize) }; }""")
    pg.evaluate("()=>{ const sect=document.querySelector('#stage .profile-stats-tab .stx-recent'); const btns=[...sect.querySelectorAll('button')].filter(b=>!b.closest('.thx-list')); btns[btns.length-1].click(); }")
    pg.wait_for_timeout(900)
    opened = pg.evaluate("()=>!!document.querySelector('#stage .screen-testhistory')")
    ck("(4) Test history: none in the heading, a row under the last test, its width, 56px+, a tile, 18px - and it opens the history (%s, %s)" % (th, opened),
       th and th.get("headBtn") == 0 and th.get("below") and th.get("wDiff", 99) <= 2 and th.get("lDiff", 99) <= 2 and th.get("h", 0) >= 56 and th.get("tile", 0) >= 32 and th.get("label", 0) >= 18 and opened, th)
    # (5) Profile's rows
    pg.evaluate("()=>{ showHome(); showProfile('profile'); window.scrollTo(0,0); }"); pg.wait_for_timeout(1200)
    rows = pg.evaluate("""()=>['.profile-customize-btn', '.pf-case-count', '.pf-goal-foot'].map(sel=>{ const b=document.querySelector('#stage '+sel); if(!b) return null;
      const c=getComputedStyle(b), r=b.getBoundingClientRect(), tile=b.querySelector('.settings-row-icon'), lab=b.querySelector('.pf-act-label'), chev=b.querySelector('.pf-act-chev svg');
      return { sel, w: Math.round(r.width), h: Math.round(r.height), bg: c.backgroundColor, rim: c.borderTopColor, rimW: parseFloat(c.borderTopWidth), tile: tile ? Math.round(tile.getBoundingClientRect().width) : 0,
               label: lab ? parseFloat(getComputedStyle(lab).fontSize) : 0, chev: !!chev }; })""")
    badr = []
    for rw in rows:
        if not rw: badr.append("missing"); continue
        bg = rgb(rw["bg"]); rim = rgb(rw["rim"])
        dark = len(bg) >= 3 and lum(bg) < .1
        lightrim = rw["rimW"] >= 1 and len(rim) >= 3 and min(rim[:3]) >= 200
        if not (dark and lightrim and rw["tile"] >= 32 and rw["label"] >= 18 and rw["chev"] and rw["h"] >= 56): badr.append(rw)
    wide = rows[0] and rows[1] and abs(rows[0]["w"] - rows[1]["w"]) <= 10
    opens = []
    for sel, scr in (("#stage .profile-customize-btn", ".screen-customize"), ("#stage .pf-case-count", ".screen-ranks"), ("#stage .pf-goal-foot", ".screen-ranks")):
        pg.evaluate("()=>{ showHome(); showProfile('profile'); }"); pg.wait_for_timeout(900)
        pg.evaluate("(s)=>{ const b=document.querySelector(s); b && b.click(); }", sel); pg.wait_for_timeout(900)
        opens.append(pg.evaluate("(s)=>!!document.querySelector('#stage ' + s)", scr))
    ck("(5) Profile's three are rows: dark glass with a rim, a tile, 18px, a chevron (%s); the case's as wide as Customize's (%s); each opens (%s)"
       % ([(r and (r["w"], r["tile"], r["label"])) for r in rows], wide, opens), not badr and wide and all(opens), badr[:2])
    # (3) iPad
    pg.set_viewport_size({"width": 834, "height": 1194}); pg.evaluate("()=>{ showHome(); showProfile('stats'); }"); pg.wait_for_timeout(1300)
    g2 = pg.evaluate(LINES); bad2 = judge_lines(g2, False)
    ck("(3) iPad: one row of four, an upright between each pair, nothing across", not bad2, bad2[:2])
    ck("(6) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
