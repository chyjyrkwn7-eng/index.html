"""Build 384: a grouped list's hairlines stop where the row's content stops - they never run to the card's edge.
Madison, with Delta's Settings beside ours: "Pay attention to their lines. Theirs don't touch the sides, why would ours? Come on,
please pay attention to details. Please ensure ours looks this great". Delta's line runs from the words to the chevron's right
edge, the row's own padding clear of the card on the right as well as the left.
Installed on an iPhone 17 Pro Max (440x956), dark, read off the page - every line between two rows (a 1px pseudo-element) on:
Settings, Settings' Sound page and Studying page (the switch rows), Contributors, Customize, and the Leaderboard's grouped list:
(1) the line's right end is at the row's content edge - the row's right side less its padding, where its chevron, switch, value
    or points end (a row of words alone, a Support link, ends there too, as Delta's do) - within 1.5px;
(2) ...and so it is clear of the card's right edge by at least 8px (it never touches the side);
(3) its left end is clear of the card's left edge as well (from the words, as before);
(4) every screen named has at least one line to measure, and no page errors;
(5) (384) every line is drawn in a colour you can see (its alpha above 0) - the Leaderboard's were transparent from 383 to 384.
Run:  python3 tools/check-b384-hairlines.py   (--against: copy the old index.html over first, as check-b382-board)"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
_s = open(HERE + "/check-b382-board.py").read()
G = {"__file__": HERE + "/check-b382-board.py", "__name__": "b384hl"}
exec(_s[:_s.index("\nwith sync_playwright() as pw:")], G)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
SCREENS = [("Settings", "showAppearance()"), ("Sound", "showAppearance({page:'sound'})"), ("Studying", "showAppearance({page:'study'})"),
           ("Contributors", "showCredits()"), ("Customize", "showCustomize()"), ("Leaderboard", "leaderboardRows=__fill(); showRankings()")]
LINES = """()=>{ const stage=document.getElementById('stage'); const out=[];
  const card=e=>{ let c=e.parentElement; while(c && c!==stage){ const s=getComputedStyle(c); if(parseFloat(s.borderTopLeftRadius)>6 && s.backgroundColor!=='rgba(0, 0, 0, 0)' && c.getBoundingClientRect().height > e.getBoundingClientRect().height + 4) return c; c=c.parentElement; }
    return e.parentElement; };
  for(const row of stage.querySelectorAll('*')){
    const r=row.getBoundingClientRect(); if(!r.width || !r.height || r.bottom < 0 || r.top > innerHeight * 3) continue;
    for(const pe of ['::before','::after']){
      const s=getComputedStyle(row, pe); if(s.content==='none'||s.content==='normal'||s.display==='none'||s.position!=='absolute') continue;
      const h=parseFloat(s.height), w=parseFloat(s.width); if(!(h>0 && h<=1.6 && w>40) || s.backgroundColor==='rgba(0, 0, 0, 0)') continue;
      if(!(Math.abs(parseFloat(s.top)) < 1 || Math.abs(parseFloat(s.bottom)) < 1)) continue;   /* a line along the row's top or bottom */
      const x0=r.left + parseFloat(s.left) + parseFloat(getComputedStyle(row).borderLeftWidth), x1=x0 + w;
      const rs=getComputedStyle(row); const cRight=r.right - parseFloat(rs.borderRightWidth) - parseFloat(rs.paddingRight);
      const c=card(row).getBoundingClientRect();
      const cls=(typeof row.className==='string'?row.className:'').trim().split(/\\s+/).slice(0,2).join('.');
      /* (384) and drawn in something: 383's clean look made --surface-border transparent beyond Home, and a line mixed from it was
         there and drawn in nothing (a computed 'color(srgb 0 0 0 / 0)' is not the 'rgba(0, 0, 0, 0)' this used to test for) */
      const bg=s.backgroundColor; let al=1; let m=/rgba\([^)]*,\s*([\d.]+)\)/.exec(bg); if(m) al=+m[1]; else { m=/color\([^)]*\/\s*([\d.]+)\)/.exec(bg); if(m) al=+m[1]; }
      out.push({ row: row.tagName.toLowerCase()+'.'+cls+pe, end: Math.round((cRight-x1)*10)/10, clearR: Math.round((c.right-x1)*10)/10, clearL: Math.round((x0-c.left)*10)/10, alpha: al });
    }
  }
  return out; }"""
with sync_playwright() as pw:
    br, ctx, pg = G["load"](pw, "promax")
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    res = {}
    for name, js in SCREENS:
        pg.evaluate("()=>{ %s; window.scrollTo(0,0); }" % js); pg.wait_for_timeout(1800)
        for _ in range(2): pg.evaluate(G["CLEAR"]); pg.wait_for_timeout(200)
        res[name] = pg.evaluate(LINES)
    # (5) This Week: the one number on each row ends where the row's content (and its line) ends
    pg.evaluate("()=>{ leaderboardRows=__fill(); showRankings(); }"); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{ const b=[...document.querySelectorAll('#stage button, #stage [role=tab]')].find(x=>/This Week/.test(x.textContent)); b && b.click(); }"); pg.wait_for_timeout(1500)
    for _ in range(2): pg.evaluate(G["CLEAR"]); pg.wait_for_timeout(200)
    week = pg.evaluate("""()=>[...document.querySelectorAll('#stage .rank-row')].map(r=>{ const c=r.querySelector('.rank-cols.rank-cols-one'); if(!c || !c.children.length) return null;
      const k=c.children[c.children.length-1], g=document.createRange(); g.selectNodeContents(k); const t=g.getBoundingClientRect(), rr=r.getBoundingClientRect(), rs=getComputedStyle(r);
      return { n:(k.textContent||'').trim(), off: Math.round((rr.right-parseFloat(rs.paddingRight)-parseFloat(rs.borderRightWidth)-t.right)*10)/10 }; }).filter(Boolean)""")
    br.close()
for name, _ in SCREENS:
    L = res[name]
    off = [l for l in L if abs(l["end"]) > 1.5]
    chk("(1) %s: %d line(s) end at the row's content edge - chevron, switch, value (off by %s)" % (name, len(L), sorted(set(l["end"] for l in L))), L and not off, off[:4])
    near = [l for l in L if l["clearR"] < 8]
    chk("(2) %s: ...clear of the card's right edge (%s px)" % (name, sorted(set(l["clearR"] for l in L))), L and not near, near[:4])
    nearL = [l for l in L if l["clearL"] < 8]
    chk("(3) %s: ...and of its left edge (%s px)" % (name, sorted(set(l["clearL"] for l in L))), L and not nearL, nearL[:4])
for name, _ in SCREENS:
    L = res[name]; faint = [l for l in L if not l["alpha"] > .03]
    chk("(5) %s: every line is drawn in a colour you can see (alpha %s) (384)" % (name, sorted(set(l["alpha"] for l in L))), L and not faint, faint[:3])
offw = [w for w in week if abs(w["off"]) > 1]
chk("(6) This Week: each row's number ends at the row's content edge, where its line ends (%d rows, off by %s)" % (len(week), sorted(set(w["off"] for w in week))[:6]),
    len(week) >= 5 and not offw, offw[:4])
chk("(4) every screen had lines to measure (%s), no page errors (%s)" % ({n: len(res[n]) for n, _ in SCREENS}, errs[:2]), all(res[n] for n, _ in SCREENS) and not errs)
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
