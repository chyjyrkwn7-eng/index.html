"""Build 384: Settings in Delta's proportions, with its hairlines; the theme's own colour at the foot.
Madison, with Delta's Settings beside ours: "Our sections for the tabs a little smaller than the delta inspection, so our icons are
smaller too, our icons don't look as nice/hd/crispy either. It's also missing the lines in between each one like delta has it. Even
our words are smaller. You see how ours has the gold text and the word nova in the default color? That needs to match your theme
too.. would be a nice touch. The word nova 'Davis' is like white and bold. Make that entire 'made by Davis' cohesive there."
iPhone 17 Pro Max (440x956), dark, Settings:
(1) (384 r5, Delta's numbers) the rows are 49-53px, their tiles 27-29px, their glyphs' drawings 55-85% of the tile (384.110: read as
    the ink, the svg being the tile's own 28 grid now) on one stroke weight of 1.18-1.36px as drawn (384.110: Delta's 1.23-1.33pt),
    their labels 15-16.5px;
(2) between two rows of a card a hairline shows (white, 8%+), starting at the label (an icon row) and running to the row's content
    edge - (384, round 2) "Theirs don't touch the sides, why would ours?": clear of the card's edge by the row's padding;
(3) the theme's colour at the foot: the Support links, the NOVA wordmark's middle and both halves of "MADE BY DAVIS" are in the
    theme's signature - not the near-gold planet highlight they were; in Amethyst they are violet, in Default its coral-rose, and the
    two themes differ; "MADE BY" and "DAVIS" are the same hue;
(5) and the pages Settings opens ("When clicking the tabs and getting in them too, ensure that stuff within them is updated too"):
    on Sound & Haptics, Study, Motion & Effects and Leaderboard & Privacy every switch row is 49px+, (384 r8) with NO tile, its title
    15-16.5px and its description 12-13.5px, and between two switch rows a hairline shows (white, 8%+) from the title to the row's content edge (the switch's); Account's
    name row and Sign out are 49-54px at 15-16.5px; Advanced's red rows 15px+; every Contributors row 15px+; Legal / Terms / Privacy text 16px;
    the sync code's label 15-16.5px and still blue;
(6) (384 r8) "when you click a section and open it, there are icons within them? But there shouldn't be.." - Delta's pages are plain
    grouped lists. On EVERY page Settings opens, in BOTH classes (Sound, Study, Motion, Account, Classes, Sync - with its code, offline
    and with no code -, Leaderboard & Privacy, Share & Install, Advanced, Contributors, Legal, Terms, Privacy): no tile shows, and every
    row's words start at the card's left padding (read off the menu: its tile's offset in its card), a one-line row is the menu's row
    height, labels are the menu's label size and second lines its second-line size, a hairline between two rows runs from the words to
    the row's content edge (clear of the card's), and every switch and chevron sits on its row's middle; tap targets 44px+;
(7) and the top-level menu keeps its tiles, in both classes: every category row (and Check for update / Advanced) carries a visible
    27-29px tile (this one cannot fail on the build before - it passes there too; it is run against a build with every tile stripped);
(4) no page errors.
Run:  python3 tools/check-b384-settings.py   (--against OLD/index.html must FAIL)"""
import os, sys, re, colorsys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b382-savecode.py")).read().split("\nwith sync_playwright() as pw:")[0]
g = {"__file__": os.path.join(HERE, "check-b382-savecode.py"), "__name__": "b384s"}
exec(src, g)
from playwright.sync_api import sync_playwright
fails = g["fails"] = []
ck = g["ck"]
def rgb(s):
    m = [float(x) for x in re.findall(r"[\d.]+", s or "")[:3]]
    if not m: return None
    return [x * 255 for x in m] if (s or "").startswith("color(") else m
def hue(c):
    if not c: return None
    h, l, s_ = colorsys.rgb_to_hls(*[v / 255 for v in c]); return (round(h * 360), round(s_, 2), round(l, 2))
def hdist(a, b): return min(abs(a - b), 360 - abs(a - b))
FOOT = """()=>{ const link=document.querySelector('#stage .settings-linkrow'); const wm=document.querySelector('#stage .settings-wordmark-text');
  const by=document.querySelector('#stage .settings-madeby-by'), nm=document.querySelector('#stage .settings-madeby-name');
  const stops = wm ? (getComputedStyle(wm).backgroundImage.match(/(rgba?|color)\\([^)]*\\)/g) || []) : [];
  return { link: link && getComputedStyle(link).color, wmMid: stops[1] || null, by: by && getComputedStyle(by).color, name: nm && getComputedStyle(nm).color }; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    errs = []
    ctx, pg = g["open_page"](br, g["init_account"]("", g["store"]()), errs=errs)
    pg.evaluate("()=>{ theme.accent='ink'; applyTheme(); showAppearance(); }"); pg.wait_for_timeout(1300)
    m = pg.evaluate("""()=>{ const rows=[...document.querySelectorAll('#stage .settings-list > .settings-row')].filter(r=>r.querySelector('.settings-row-icon'));
      if(rows.length < 2) return { h: 0, tile: 0, glyph: 0, label: 0, strokes: [], sepBg: '', sepLeft: 0, labelLeft: 99, sepRight: 0, cardRight: 0, contentRight: 99, none: true };   /* (384 r8) a menu with no tiled rows fails (1)/(2), it does not stop the gate */
      const r=rows[0], ic=r.querySelector('.settings-row-icon'), sv=ic.querySelector('svg'), lab=r.querySelector('.settings-row-label');
      /* (384.110) the stroke as drawn: its width times the scale it is drawn at (a glyph drawn a touch larger divides its stroke by that scale) */
      const parts=[...sv.querySelectorAll('path, circle, rect, line, polyline')].filter(e=>!e.closest('defs, clipPath')).map(e=>{ const m=e.getScreenCTM(); return parseFloat(getComputedStyle(e).strokeWidth)*Math.sqrt(Math.abs(m.a*m.d-m.b*m.c)); }).filter(v=>v>0);
      /* (384.110) the glyph's drawing, not its box: the svg is the tile's own 28 grid now; the ink (getBBox + the stroke) */
      let ink=0; { let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9; for(const e of sv.querySelectorAll('path, circle, rect, line, polyline')){ if(e.closest('defs, clipPath')) continue; const b=e.getBBox(), m=e.getScreenCTM();
        const xs=[m.a*b.x+m.e, m.a*(b.x+b.width)+m.e], ys=[m.d*b.y+m.f, m.d*(b.y+b.height)+m.f]; x0=Math.min(x0,...xs); x1=Math.max(x1,...xs); y0=Math.min(y0,...ys); y1=Math.max(y1,...ys); }
        ink=Math.max(x1-x0, y1-y0) + (parts.length ? parts[0] : 0); }
      const b=rows[1], sep=getComputedStyle(b,'::before'), lr=b.querySelector('.settings-row-label').getBoundingClientRect(), br=b.getBoundingClientRect(), card=b.parentElement.getBoundingClientRect();
      return { h: r.getBoundingClientRect().height, tile: ic.getBoundingClientRect().width, glyph: ink, label: parseFloat(getComputedStyle(lab).fontSize),
               strokes: [...new Set(parts.map(v=>Math.round(v*100)/100))], sepBg: sep.backgroundColor, sepLeft: br.left + parseFloat(sep.left), labelLeft: lr.left,
               sepRight: br.right - parseFloat(sep.right || '0'), cardRight: card.right,
               contentRight: br.right - parseFloat(getComputedStyle(b).paddingRight) - parseFloat(getComputedStyle(b).borderRightWidth) }; }""")
    ck("(1) rows %spx, tiles %spx, glyph ink %spx on one stroke %s, labels %spx" % (m["h"], m["tile"], round(m["glyph"], 1), m["strokes"], m["label"]),
       49 <= m["h"] <= 53 and 27 <= m["tile"] <= 29 and .55 * m["tile"] <= m["glyph"] <= .85 * m["tile"] and m["strokes"] and max(m["strokes"]) - min(m["strokes"]) <= .03 and 1.18 <= m["strokes"][0] <= 1.36 and 15 <= m["label"] <= 16.5, m)   # (384.110) Delta's glyph stroke off the new screenshots: 1.23-1.33pt (it was held at 1.5+ here); the drawing 55-85% of the tile, read as ink   # (384 r5) Delta measured off his two screenshots: row 51, tile 27.6, label ~15.5   # (384 r5: one even weight - the lighter 1.75 of the glass tiles)
    sa = re.findall(r"[\d.]+", m["sepBg"] or ""); alpha = float(sa[3]) if len(sa) > 3 else (1 if sa else 0)
    ck("(2) a hairline between rows (%s), from the label (%s / %s) to the row's content edge (%s / %s), clear of the card's (%s)" % (m["sepBg"], round(m["sepLeft"]), round(m["labelLeft"]), round(m["sepRight"]), round(m["contentRight"]), round(m["cardRight"])),
       alpha >= .08 and abs(m["sepLeft"] - m["labelLeft"]) <= 2 and abs(m["sepRight"] - m["contentRight"]) <= 2 and m["cardRight"] - m["sepRight"] >= 8, m)
    out = {}
    for acc in ("ink", "elite"):
        pg.evaluate("(a)=>{ theme.accent=a; applyTheme(); showAppearance(); }", acc); pg.wait_for_timeout(900)
        out[acc] = pg.evaluate(FOOT)
    gold = hue([255, 211, 122])
    hues = {a: {k: hue(rgb(v)) for k, v in out[a].items()} for a in out}
    ink, el = hues["ink"], hues["elite"]
    violet = lambda h: h and 250 <= h[0] <= 300
    cohesive = all(hues[a]["by"] and hues[a]["name"] and hdist(hues[a]["by"][0], hues[a]["name"][0]) <= 20 and hues[a]["by"][1] >= .2 for a in hues)
    ck("(3) the foot in the theme's colour: Amethyst violet %s, Default not the gold %s (%s), the two differ, MADE BY and DAVIS one hue" % (el, gold, ink),
       all(violet(el[k]) for k in ("link", "wmMid", "by", "name")) and all(ink[k] and hdist(ink[k][0], gold[0]) > 15 for k in ("link", "wmMid", "name"))
       and hdist(ink["link"][0], el["link"][0]) > 40 and cohesive, [out, hues])
    pg.evaluate("()=>{ theme.accent='ink'; applyTheme(); }")
    SW = """()=>{ const rows=[...document.querySelectorAll('#stage .screen-settings-sub .settings-card > label.opt')].filter(r=>r.getBoundingClientRect().height>0);
      return rows.map((r,i)=>{ const t=r.querySelector('.otext'), h=r.querySelector('.ohint'), ic=[...r.querySelectorAll('.settings-row-icon')].find(e=>e.getBoundingClientRect().width>0), card=r.parentElement.getBoundingClientRect();
        const prev=r.previousElementSibling, sep=getComputedStyle(r,'::before'), rr=r.getBoundingClientRect(), tr=t.getBoundingClientRect();
        const between = !!(prev && prev.matches('label.opt, .settings-volume'));
        return { h: Math.round(rr.height), title: parseFloat(getComputedStyle(t).fontSize), hint: h ? parseFloat(getComputedStyle(h).fontSize) : 99, tile: ic ? Math.round(ic.getBoundingClientRect().width) : 99,
                 between, sep: between ? sep.backgroundColor : null, sepL: between ? Math.round(rr.left + parseFloat(sep.left)) : null, titleL: Math.round(tr.left),
                 sepR: between ? Math.round(rr.right - parseFloat(sep.right)) : null, cardR: Math.round(card.right),
                 contR: Math.round(rr.right - parseFloat(getComputedStyle(r).paddingRight) - parseFloat(getComputedStyle(r).borderRightWidth)) }; }); }"""
    def alpha_of(c):
        a = re.findall(r"[\d.]+", c or ""); return float(a[3]) if len(a) > 3 else (1 if a else 0)
    bad = []
    for page in ("sound", "study", "motion", "rankings"):
        pg.evaluate("(p)=>showAppearance({ page: p })", page); pg.wait_for_timeout(800)
        for r in pg.evaluate(SW):
            okr = 49 <= r["h"] <= 140 and 15 <= r["title"] <= 16.5 and 12 <= r["hint"] <= 13.5 and r["tile"] == 99   # (384 r8) no tile on a page
            if r["between"]: okr = okr and alpha_of(r["sep"]) >= .08 and abs(r["sepL"] - r["titleL"]) <= 2 and abs(r["sepR"] - r["contR"]) <= 2 and r["cardR"] - r["sepR"] >= 8
            if not okr: bad.append((page, r))
    pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(800)
    acc = pg.evaluate("""()=>{ const n=document.querySelector('#stage .customize-namerow'), d=n && n.querySelector('.profile-name-display'), so=document.querySelector('#stage .signout-row');
      return { nameH: n ? Math.round(n.getBoundingClientRect().height) : 0, name: d ? parseFloat(getComputedStyle(d).fontSize) : 0,
               chg: (n && n.querySelector('.profile-edit-btn')) ? (()=>{ const b=n.querySelector('.profile-edit-btn'), r=b.getBoundingClientRect(); return { h: Math.round(r.height), f: parseFloat(getComputedStyle(b).fontSize) }; })() : null,
               outH: so ? Math.round(so.getBoundingClientRect().height) : 0, out: so ? parseFloat(getComputedStyle(so.querySelector('.settings-row-label')).fontSize) : 0 }; }""")
    # (384 r16) "why is the name and change button so tiny": the name reads at 16-18px and Change is a real button (words 15.5px+, 36px+ tall)
    if not (49 <= acc["nameH"] <= 58 and 16 <= acc["name"] <= 18 and acc["chg"] and acc["chg"]["f"] >= 15.5 and acc["chg"]["h"] >= 36 and 49 <= acc["outH"] <= 54 and 15 <= acc["out"] <= 16.5): bad.append(("account", acc))
    pg.evaluate("()=>showAppearance({ page: 'sync' })"); pg.wait_for_timeout(800)
    sy = pg.evaluate("()=>{ const l=document.querySelector('#stage .sync-code-label'); return l ? { size: parseFloat(getComputedStyle(l).fontSize), color: getComputedStyle(l).color } : null; }")
    sh = hue(rgb(sy and sy["color"]))
    if not (sy and 15 <= sy["size"] <= 16.5 and sh and 195 <= sh[0] <= 215): bad.append(("sync", sy, sh))
    pg.evaluate("()=>showAdvancedSettings()"); pg.wait_for_timeout(800)
    adv = pg.evaluate("()=>[...document.querySelectorAll('#stage .settings-textrow')].map(r=>parseFloat(getComputedStyle(r).fontSize))")
    if not adv or min(adv) < 15: bad.append(("advanced", adv))
    pg.evaluate("()=>showCredits()"); pg.wait_for_timeout(800)
    cr = pg.evaluate("""()=>[...document.querySelectorAll('#stage .credits-card > .credits-item')].map(r=>{ const l=r.querySelector('.settings-row-label') || r; return parseFloat(getComputedStyle(l).fontSize); })
      .concat([...document.querySelectorAll('#stage .credits-name')].map(n=>parseFloat(getComputedStyle(n).fontSize)))""")
    if not cr or min(cr) < 15: bad.append(("credits", sorted(set(cr))))
    for kind in ("legal", "terms", "privacy"):
        pg.evaluate("(k)=>showSettingsText(k)", kind); pg.wait_for_timeout(700)
        pr = pg.evaluate("()=>[...document.querySelectorAll('#stage .settings-prose > p')].map(p=>parseFloat(getComputedStyle(p).fontSize))")
        if not pr or min(pr) < 16: bad.append((kind, sorted(set(pr))))
    ck("(5) the pages Settings opens: switch rows (no tile), Account, the sync code, Advanced, Contributors and Legal/Terms/Privacy at the menu's size, hairlines between switch rows",
       not bad, bad[:4])
    ctx.close()

    # ---- (6) / (7): every page, both classes (384 r8) ----
    MENU_REF = """()=>{ const vis=e=>{ const b=e.getBoundingClientRect(); return b.width>0 && b.height>0; };
      const cats=[...document.querySelectorAll('#stage .screen-settings .settings-list > button.settings-row')].filter(vis)
        .filter(r=>!r.matches('.settings-plainrow, .settings-linkrow, .settings-textrow'));
      const t=r=>{ const i=r.querySelector(':scope > .settings-row-icon'); return i && vis(i) ? i.getBoundingClientRect() : null; };
      const one=cats.find(r=>t(r) && !r.querySelector('.settings-row-sub'));
      const sub=document.querySelector('#stage .screen-settings .settings-list .settings-row-sub');
      const lab=one && one.querySelector('.settings-row-label');
      return { cats: cats.map(r=>({ name: (r.querySelector('.settings-row-label')||r).textContent.trim().slice(0,30), cat: r.classList.contains('settings-cat'), tile: t(r) ? Math.round(t(r).width*10)/10 : 0 })),
               pad: one ? t(one).left - one.closest('.settings-card').getBoundingClientRect().left : null, rowH: one ? one.getBoundingClientRect().height : null,
               label: lab ? parseFloat(getComputedStyle(lab).fontSize) : null, sub: sub ? parseFloat(getComputedStyle(sub).fontSize) : null }; }"""
    SUB = r"""()=>{ const S=document.querySelector('#stage .screen-settings-sub'); if(!S) return null;
      const vis=e=>{ const b=e.getBoundingClientRect(); if(!b.width||!b.height) return false;
        for(let x=e; x && x.nodeType===1; x=x.parentElement){ const cs=getComputedStyle(x); if(cs.display==='none'||cs.visibility==='hidden'||parseFloat(cs.opacity)===0) return false; } return true; };
      const tiles=[...S.querySelectorAll('.settings-row-icon, [data-tile]')].filter(vis).map(e=>(e.parentElement.textContent||'').trim().slice(0,30));
      const RS='.settings-card .settings-row, .settings-card > label.opt, .settings-card .sync-code-row';
      const rows=[...S.querySelectorAll(RS)].filter(vis);
      const firstText=r=>{ const w=document.createTreeWalker(r, NodeFilter.SHOW_TEXT); let n;
        while((n=w.nextNode())){ if(!n.nodeValue.trim()) continue; if(n.parentElement.closest('.box, .settings-row-value, .settings-row-chev')) continue; return n; } return null; };
      const al=c=>{ const a=(c||'').match(/[\d.]+/g)||[]; return a.length>3 ? +a[3] : (a.length ? 1 : 0); };
      const mid=b=>b.top+b.height/2;
      return { tiles, rows: rows.map(r=>{
        const card=r.closest('.settings-card').getBoundingClientRect(), rb=r.getBoundingClientRect(), rs=getComputedStyle(r);
        const tn=firstText(r); let tl=null, fs=null, tc=null;
        if(tn){ const g=document.createRange(); g.selectNodeContents(tn); const tb=g.getBoundingClientRect(); tl=tb.left; tc=tb.left+tb.width/2; fs=parseFloat(getComputedStyle(tn.parentElement).fontSize); }
        /* how many lines of words the row holds (a name over its role is two, with no .settings-row-sub) */
        const tops=[]; { const w=document.createTreeWalker(r, NodeFilter.SHOW_TEXT); let n;
          while((n=w.nextNode())){ if(!n.nodeValue.trim() || n.parentElement.closest('.box, .settings-row-chev') || !vis(n.parentElement)) continue;
            const g=document.createRange(); g.selectNodeContents(n); for(const q of g.getClientRects()) if(q.width>1 && !tops.some(t=>Math.abs(t-q.top)<5)) tops.push(q.top); } }
        const sub=r.querySelector('.settings-row-sub, .ohint');
        const prev=r.previousElementSibling;
        const between=!!(prev && vis(prev) && prev.matches('.settings-row, label.opt, .settings-volume'));
        const pe=getComputedStyle(r,'::before'); const ph=parseFloat(pe.height);
        const line = (pe.content!=='none' && pe.content!=='normal' && pe.position==='absolute' && ph>0 && ph<=1.6) ? (()=>{ const x0=rb.left+parseFloat(rs.borderLeftWidth)+parseFloat(pe.left); return { l:x0, r:x0+parseFloat(pe.width), a:al(pe.backgroundColor) }; })() : null;
        const chev=r.querySelector(':scope > .settings-row-chev'), sw=r.querySelector(':scope > .box');
        return { name: tn ? tn.nodeValue.trim().slice(0,30) : '', h: rb.height, tl, fs, lines: tops.length,
          centred: tc !== null && Math.abs(tc-(rb.left+rb.width/2)) < 2, sub: sub ? parseFloat(getComputedStyle(sub).fontSize) : null,
          tap: r.matches('button, label') ? Math.min(rb.width, rb.height) : null, cardL: card.left, cardR: card.right,
          contR: rb.right-parseFloat(rs.paddingRight)-parseFloat(rs.borderRightWidth), between, line,
          chevOff: chev && vis(chev) ? mid(chev.getBoundingClientRect())-mid(rb) : null, swOff: sw && vis(sw) ? mid(sw.getBoundingClientRect())-mid(rb) : null }; }) }; }"""
    STATES = [("sound", "showAppearance({page:'sound'})"), ("study", "showAppearance({page:'study'})"), ("motion", "showAppearance({page:'motion'})"),
              ("account", "showAppearance({page:'account'})"), ("classes", "showAppearance({page:'classes'})"), ("sync", "showAppearance({page:'sync'})"),
              ("rankings", "showAppearance({page:'rankings'})"), ("share", "showAppearance({page:'share'})"), ("advanced", "showAdvancedSettings()"),
              ("credits", "showCredits()"), ("legal", "showSettingsText('legal')"), ("terms", "showSettingsText('terms')"), ("privacy", "showSettingsText('privacy')"),
              # Sync once the cloud answers (no "isn't reachable" row), then with no code at all (Start syncing / Enter a code)
              ("sync-online", "__fake(); showAppearance({page:'sync'})"), ("sync-nocode", "syncCode=null; showAppearance({page:'sync'})")]
    IFC_INIT = g["init_account"]("GATE-0384", g["store"](publicId="xph5b57jbp5a", classes=["academy", "ifc"])) + \
        "localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.greet.ifc','done');"
    bad6, bad7, seen6 = [], [], {}
    for cls, init in (("academy", g["init_account"]("GATE-0384", g["store"]())), ("ifc", IFC_INIT)):
        ctx, pg = g["open_page"](br, init, errs=errs)
        if cls == "ifc" and pg.evaluate("()=>window.NOVA_CLASS") != "ifc": bad6.append((cls, "the page did not open in Fire Code")); ctx.close(); continue
        pg.evaluate("()=>{ theme.accent='ink'; applyTheme(); showAppearance(); }"); pg.wait_for_timeout(1100)
        ref = pg.evaluate(MENU_REF)
        if not ref["cats"] or not ref["pad"]: bad7.append((cls, "no menu", ref)); ctx.close(); continue
        nocat = [c["name"] for c in ref["cats"] if not (27 <= c["tile"] <= 29)]
        if nocat or sum(1 for c in ref["cats"] if c["cat"]) < 6: bad7.append((cls, "menu rows without a tile", nocat, len(ref["cats"])))
        for name, js in STATES:
            pg.evaluate("()=>{ %s; }" % js); pg.wait_for_timeout(900)
            m = pg.evaluate(SUB)
            if not m: bad6.append((cls, name, "no page")); continue
            seen6[cls + ":" + name] = (len(m["rows"]), len(m["tiles"]))
            if m["tiles"]: bad6.append((cls, name, "tiles", m["tiles"][:4]))
            for r in m["rows"]:
                why = []
                if r["centred"]: pass   # a centred action (Sign out of Nova) has no left edge to line up: its words sit on the row's middle
                elif r["tl"] is None or abs((r["tl"] - r["cardL"]) - ref["pad"]) > 1.5: why.append("words at %s, not the card's padding %s" % (r["tl"] and round(r["tl"] - r["cardL"], 1), round(ref["pad"], 1)))
                if r["lines"] == 1 and not (abs(r["h"] - ref["rowH"]) <= 1.5): why.append("one line %spx, not the menu's %spx" % (round(r["h"], 1), round(ref["rowH"], 1)))
                if r["h"] < ref["rowH"] - 1.5: why.append("%spx, under the menu's row" % round(r["h"], 1))
                if r["fs"] and not (abs(r["fs"] - ref["label"]) <= .6): why.append("label %spx, not %spx" % (r["fs"], ref["label"]))
                if r["sub"] is not None and ref["sub"] and not (abs(r["sub"] - ref["sub"]) <= .6): why.append("second line %spx, not %spx" % (r["sub"], ref["sub"]))
                if r["tap"] is not None and r["tap"] < 44: why.append("tap %spx" % round(r["tap"]))
                if r["between"]:
                    L = r["line"]
                    if not L or L["a"] < .08: why.append("no hairline above")
                    elif abs(L["l"] - r["tl"]) > 2 or abs(L["r"] - r["contR"]) > 2 or r["cardR"] - L["r"] < 8:
                        why.append("hairline %s..%s, words at %s, content edge %s, card %s" % (round(L["l"]), round(L["r"]), round(r["tl"] or 0), round(r["contR"]), round(r["cardR"])))
                for k in ("chevOff", "swOff"):
                    if r[k] is not None and abs(r[k]) > 1: why.append("%s %+.1fpx off the row's middle" % ("chevron" if k == "chevOff" else "switch", r[k]))
                if why: bad6.append((cls, name, r["name"], why))
        ctx.close()
    print("     rows (and tiles) read per page:", seen6)
    for b in bad6[:40]: print("     ", b)
    ck("(6) no tile on any page Settings opens, in either class; words at the card's padding, Delta's sizes, hairlines under the words, switches and chevrons centred",
       not bad6 and len(seen6) >= 2 * len(STATES) and all(v[0] for k, v in seen6.items() if not k.endswith((":legal", ":terms", ":privacy")) and k != "ifc:sync-nocode"), bad6)   # prose pages; Fire Code with no code is a line of words
    ck("(7) the top-level menu keeps its tiles, in both classes", not bad7, bad7[:4])
    ck("(4) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
