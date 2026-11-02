"""Build 382: the Leaderboard and the Calendar in Settings' language (the clean iOS look).
Shape, read off the page, on a Pro Max (440x956), a Pro Max at 85% zoom (518x1125), an SE (375x667), an iPad 11 (834x1194) and a
laptop (1440x900):
(1) the page title is big and bold: the header's word (Leaderboard / Calendar) is at least 1.6x the body text and bold (>= 700);
(2) the board switch is a segmented control: one track, its segments side by side in one row, each >= 44px tall, the track spans
    most of the column (>= 80% of the rows' width), no frost on it;
(3) the list is grouped: from fourth place down the rows touch (no gap between neighbours), only the group's first row has top
    corners and only its last bottom corners, a hairline (::after, 1px) under every row but the last, starting right of the row's
    left edge (inset to the name), every row >= 44px, and no row carries a backdrop-filter;
(4) the top three are cards of their own (rounded all round, a gap under each);
(5) the search field and Find me are each >= 44px tall, the field's placeholder starts at the left;
(6) the calendar: today's number is a circle in the accent (filled when picked), the cards carry no backdrop-filter and are rounded
    >= 18px, the cards' headings are not spaced capitals, the test's topics are rows with a hairline between them;
(7) no horizontal overflow on either screen at any size.
Run:  python3 tools/check-b382-ios.py   (--against: copy the old index.html over first)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
g["DEV"].update({"pm85": (518, 1125, (62, 0, 34, 0), True), "se2": (375, 667, (20, 0, 0, 0), True), "laptop": (1440, 900, (0, 0, 0, 0), False)})
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const ids=['ninja','wizard','ghost','grizzly']; const rows=[]; for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%4]}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2), xp:90000-i*2000})); } leaderboardRows=rows; }"""
TITLE = """()=>{ const c=document.getElementById('count'); const cs=getComputedStyle(c); const body=parseFloat(getComputedStyle(document.body).fontSize);
  return { text:c.textContent, ratio: Math.round(parseFloat(cs.fontSize)/body*100)/100, weight: +cs.fontWeight }; }"""
BOARD = """()=>{ const scr=document.querySelector('.screen-rankings'); const cs=e=>getComputedStyle(e);
  const seg=scr.querySelector(':scope > .navsegment'); const btns=seg ? [...seg.querySelectorAll(':scope > .iconbtn')] : [];
  const rows=[...scr.querySelectorAll('.rank-rows > .rank-row[data-pub]')]; const rw=rows.length ? rows[0].getBoundingClientRect().width : 1;
  const sb=seg ? seg.getBoundingClientRect() : null;
  const segInfo = seg ? { tops: btns.map(b=>Math.round(b.getBoundingClientRect().top)), hs: btns.map(b=>Math.round(b.getBoundingClientRect().height*10)/10),
    span: Math.round(sb.width/rw*100)/100, blur: (cs(seg).backdropFilter||'none') } : null;
  const list=rows.filter(r=>!/rank-podium-[123]/.test(r.className));
  const R=r=>r.getBoundingClientRect(); const rad=(r,k)=>parseFloat(cs(r)[k])||0;
  const gaps=list.slice(0,10).map((r,i,a)=>i ? Math.round((R(r).top-R(a[i-1]).bottom)*10)/10 : 0).slice(1);
  const vis=list.slice(0,10);
  const corners=vis.map(r=>[rad(r,'borderTopLeftRadius'), rad(r,'borderBottomLeftRadius')]);
  const hair=vis.map(r=>{ const a=getComputedStyle(r,'::after'); return { on: a.content!=='none' && a.content!=='normal', h: parseFloat(a.height)||0, l: parseFloat(a.left)||0 }; });
  const pod=[1,2,3].map(n=>{ const r=scr.querySelector('.rank-row.rank-podium-'+n); if(!r) return null; const nx=r.nextElementSibling;
    return { tl: rad(r,'borderTopLeftRadius'), bl: rad(r,'borderBottomLeftRadius'), gap: nx ? Math.round((R(nx).top-R(r).bottom)*10)/10 : null }; });
  const search=scr.querySelector('.rank-search'); const me=scr.querySelector('.rank-me-btn');
  return { seg: segInfo, gaps, corners, hair, pod, hmin: Math.min(...rows.map(r=>R(r).height)),
    blur: rows.filter(r=>{ const f=cs(r).backdropFilter||'none'; return f!=='none'; }).length,
    search: search ? { h: R(search).height, align: cs(search).textAlign } : null, me: me ? R(me).height : null, n: rows.length,
    over: document.documentElement.scrollWidth - innerWidth }; }"""
CAL = """()=>{ const scr=document.querySelector('.screen-calendar-tab'); const cs=e=>getComputedStyle(e);
  const acc=(()=>{ const t=document.createElement('span'); t.style.color='var(--accent)'; scr.appendChild(t); const c=cs(t).color; t.remove(); return c; })();
  const tn=scr.querySelector('.cal-grid .cal-cell-today .cal-cell-num');
  const today = tn ? { bg: cs(tn).backgroundColor, color: cs(tn).color, round: (parseFloat(cs(tn).borderTopLeftRadius)||0) >= tn.getBoundingClientRect().width/2 - 1 || cs(tn).borderTopLeftRadius==='50%',
    sel: !!tn.closest('.cal-cell-sel') } : null;
  const cards=[...scr.querySelectorAll('.cal-card:not([hidden]), .cal-monthview')];
  const cardInfo=cards.map(c=>({ blur: cs(c).backdropFilter||'none', r: parseFloat(cs(c).borderTopLeftRadius)||0 }));
  const heads=[...scr.querySelectorAll('.cal-card .cal-card-head .slab')].map(h=>({ tt: cs(h).textTransform, ls: (parseFloat(cs(h).letterSpacing)||0)/parseFloat(cs(h).fontSize) }));
  const lis=[...scr.querySelectorAll('.cal-topics-list > li')];
  const lines=lis.filter(li=>li.previousElementSibling).map(li=>{ const a=cs(li).borderTopWidth!=='0px' ? 1 : (()=>{ const x=getComputedStyle(li,'::after'); return (x.content!=='none' && x.content!=='normal' && parseFloat(x.height)>=.5) ? 1 : 0; })(); return a; });
  return { acc, today, cards: cardInfo, heads, topics: lis.length, lines, over: document.documentElement.scrollWidth - innerWidth }; }"""

def load(pw, dev):
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    w, h, ins, inst = g["DEV"][dev]; g["g"]["new_page"].w, g["g"]["new_page"].h = w, h
    ctx, pg = g["g"]["new_page"](br, ins, inst, False)
    pg.add_init_script(g["INIT"] % json.dumps(g["seed"]()))
    pg.goto(g["url"]); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1200)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(250)
    return br, pg

with sync_playwright() as pw:
    for dev in ["promax", "pm85", "se2", "ipad11", "laptop"]:
        br, pg = load(pw, dev)
        pg.evaluate(FILL); pg.evaluate("()=>showRankings('overall')"); pg.wait_for_timeout(2200)
        pg.evaluate(CLEAR)
        t = pg.evaluate(TITLE); b = pg.evaluate(BOARD)
        chk("%s board: the title %r is big and bold (%sx the body, weight %s)" % (dev, t["text"], t["ratio"], t["weight"]),
            t["text"] == "Leaderboard" and t["ratio"] >= 1.6 and t["weight"] >= 700, t)
        s = b["seg"]
        chk("%s board: the switch is a segmented control - one row %s, segments %s tall, %s of the rows' width, frost %s" % (dev, s and s["tops"], s and s["hs"], s and s["span"], s and s["blur"]),
            s and len(s["tops"]) >= 3 and max(s["tops"]) - min(s["tops"]) <= 1 and min(s["hs"]) >= 44 and s["span"] >= .8 and s["blur"] == "none", s)
        hair_ok = all(x["on"] and x["h"] >= .5 and x["l"] > 8 for x in b["hair"][:-1]) if len(b["hair"]) > 1 else False
        corner_ok = len(b["corners"]) > 2 and b["corners"][0][0] >= 12 and all(c[0] == 0 for c in b["corners"][1:]) and all(c[1] == 0 for c in b["corners"][:-1])
        chk("%s board: the list is grouped - gaps between rows %s, corners %s, hairlines %s, rows >= 44px (%s), blurred rows %d" % (dev, b["gaps"][:6], b["corners"][:4], b["hair"][:3], round(b["hmin"], 1), b["blur"]),
            b["gaps"] and max(abs(x) for x in b["gaps"]) <= 0.6 and corner_ok and hair_ok and b["hmin"] >= 44 and b["blur"] == 0, b)
        chk("%s board: the top three are cards of their own %s" % (dev, b["pod"]),
            all(p and p["tl"] >= 12 and p["bl"] >= 12 and (p["gap"] or 0) >= 4 for p in b["pod"]), b["pod"])
        chk("%s board: search %s and Find me %spx are >= 44px, the field starts at the left" % (dev, b["search"], b["me"]),
            b["search"] and b["search"]["h"] >= 44 and b["me"] >= 44 and b["search"]["align"] in ("left", "start"), b)
        chk("%s board: no sideways scroll (%dpx)" % (dev, b["over"]), b["over"] <= 0, b)
        pg.evaluate("()=>showCalendar()"); pg.wait_for_timeout(1500); pg.evaluate(CLEAR)
        t = pg.evaluate(TITLE); c = pg.evaluate(CAL)
        chk("%s calendar: the title %r is big and bold (%sx, weight %s)" % (dev, t["text"], t["ratio"], t["weight"]),
            t["text"] == "Calendar" and t["ratio"] >= 1.6 and t["weight"] >= 700, t)
        td = c["today"]
        chk("%s calendar: today is the accent's circle %s (accent %s)" % (dev, td, c["acc"]),
            td and td["round"] and (td["bg"] == c["acc"] if td["sel"] else td["color"] == c["acc"]), c)
        chk("%s calendar: cards flat and round %s, headings not spaced capitals %s" % (dev, c["cards"], c["heads"]),
            c["cards"] and all(x["blur"] == "none" and x["r"] >= 18 for x in c["cards"]) and c["heads"] and all(h["tt"] == "none" and h["ls"] < .03 for h in c["heads"]), c)
        chk("%s calendar: the test's %d topics are rows with hairlines %s" % (dev, c["topics"], c["lines"]),
            c["topics"] < 2 or all(c["lines"]), c)
        chk("%s calendar: no sideways scroll (%dpx)" % (dev, c["over"]), c["over"] <= 0, c)
        br.close()
print("ALL PASS" if g["ok"] else "SOME FAILED")
sys.exit(0 if g["ok"] else 1)
