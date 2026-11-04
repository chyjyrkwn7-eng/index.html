"""Build 384: Settings in Delta's proportions, with its hairlines; the theme's own colour at the foot.
Madison, with Delta's Settings beside ours: "Our sections for the tabs a little smaller than the delta inspection, so our icons are
smaller too, our icons don't look as nice/hd/crispy either. It's also missing the lines in between each one like delta has it. Even
our words are smaller. You see how ours has the gold text and the word nova in the default color? That needs to match your theme
too.. would be a nice touch. The word nova 'Davis' is like white and bold. Make that entire 'made by Davis' cohesive there."
iPhone 17 Pro Max (440x956), dark, Settings:
(1) the rows are 58px+ tall, their tiles 32px+, their glyphs 21px+ on one stroke weight (2px+), their labels 18px+;
(2) between two rows of a card a hairline shows (white, 8%+), starting at the label (an icon row) and running to the card's edge;
(3) the theme's colour at the foot: the Support links, the NOVA wordmark's middle and both halves of "MADE BY DAVIS" are in the
    theme's signature - not the near-gold planet highlight they were; in Amethyst they are violet, in Default its coral-rose, and the
    two themes differ; "MADE BY" and "DAVIS" are the same hue;
(5) and the pages Settings opens ("When clicking the tabs and getting in them too, ensure that stuff within them is updated too"):
    on Sound & Haptics, Study, Motion & Effects and Leaderboard & Privacy every switch row is 58px+, its tile 32px+, its title 18px+
    and its description 14px+, and between two switch rows a hairline shows (white, 8%+) from the title to the card's edge; Account's
    name row and Sign out are 58px+ at 18px; Advanced's red rows 18px; every Contributors row 18px; Legal / Terms / Privacy text 16px;
    the sync code's label 18px and still blue;
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
      const r=rows[0], ic=r.querySelector('.settings-row-icon'), sv=ic.querySelector('svg'), lab=r.querySelector('.settings-row-label');
      const parts=[sv, ...sv.querySelectorAll('[stroke], path, circle, rect, line, polyline')].map(e=>parseFloat(getComputedStyle(e).strokeWidth)).filter(v=>v>0);
      const b=rows[1], sep=getComputedStyle(b,'::before'), lr=b.querySelector('.settings-row-label').getBoundingClientRect(), br=b.getBoundingClientRect(), card=b.parentElement.getBoundingClientRect();
      return { h: r.getBoundingClientRect().height, tile: ic.getBoundingClientRect().width, glyph: sv.getBoundingClientRect().width, label: parseFloat(getComputedStyle(lab).fontSize),
               strokes: [...new Set(parts.map(v=>Math.round(v*100)/100))], sepBg: sep.backgroundColor, sepLeft: br.left + parseFloat(sep.left), labelLeft: lr.left,
               sepRight: br.right - parseFloat(sep.right || '0'), cardRight: card.right }; }""")
    ck("(1) rows %spx, tiles %spx, glyphs %spx on one stroke %s, labels %spx" % (m["h"], m["tile"], m["glyph"], m["strokes"], m["label"]),
       m["h"] >= 58 and m["tile"] >= 32 and m["glyph"] >= 21 and len(m["strokes"]) == 1 and m["strokes"][0] >= 2 and m["label"] >= 18, m)
    sa = re.findall(r"[\d.]+", m["sepBg"] or ""); alpha = float(sa[3]) if len(sa) > 3 else (1 if sa else 0)
    ck("(2) a hairline between rows (%s), from the label (%s / %s) to the card's edge (%s / %s)" % (m["sepBg"], round(m["sepLeft"]), round(m["labelLeft"]), round(m["sepRight"]), round(m["cardRight"])),
       alpha >= .08 and abs(m["sepLeft"] - m["labelLeft"]) <= 2 and abs(m["sepRight"] - m["cardRight"]) <= 2, m)
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
      return rows.map((r,i)=>{ const t=r.querySelector('.otext'), h=r.querySelector('.ohint'), ic=r.querySelector('.settings-row-icon'), card=r.parentElement.getBoundingClientRect();
        const prev=r.previousElementSibling, sep=getComputedStyle(r,'::before'), rr=r.getBoundingClientRect(), tr=t.getBoundingClientRect();
        const between = !!(prev && prev.matches('label.opt, .settings-volume'));
        return { h: Math.round(rr.height), title: parseFloat(getComputedStyle(t).fontSize), hint: h ? parseFloat(getComputedStyle(h).fontSize) : 99, tile: ic ? Math.round(ic.getBoundingClientRect().width) : 99,
                 between, sep: between ? sep.backgroundColor : null, sepL: between ? Math.round(rr.left + parseFloat(sep.left)) : null, titleL: Math.round(tr.left),
                 sepR: between ? Math.round(rr.right - parseFloat(sep.right)) : null, cardR: Math.round(card.right) }; }); }"""
    def alpha_of(c):
        a = re.findall(r"[\d.]+", c or ""); return float(a[3]) if len(a) > 3 else (1 if a else 0)
    bad = []
    for page in ("sound", "study", "motion", "rankings"):
        pg.evaluate("(p)=>showAppearance({ page: p })", page); pg.wait_for_timeout(800)
        for r in pg.evaluate(SW):
            okr = r["h"] >= 58 and r["title"] >= 18 and r["hint"] >= 14 and r["tile"] >= 32
            if r["between"]: okr = okr and alpha_of(r["sep"]) >= .08 and abs(r["sepL"] - r["titleL"]) <= 2 and abs(r["sepR"] - r["cardR"]) <= 2
            if not okr: bad.append((page, r))
    pg.evaluate("()=>showAppearance({ page: 'account' })"); pg.wait_for_timeout(800)
    acc = pg.evaluate("""()=>{ const n=document.querySelector('#stage .customize-namerow'), d=n && n.querySelector('.profile-name-display'), so=document.querySelector('#stage .signout-row');
      return { nameH: n ? Math.round(n.getBoundingClientRect().height) : 0, name: d ? parseFloat(getComputedStyle(d).fontSize) : 0,
               outH: so ? Math.round(so.getBoundingClientRect().height) : 0, out: so ? parseFloat(getComputedStyle(so.querySelector('.settings-row-label')).fontSize) : 0 }; }""")
    if not (acc["nameH"] >= 58 and acc["name"] >= 18 and acc["outH"] >= 58 and acc["out"] >= 18): bad.append(("account", acc))
    pg.evaluate("()=>showAppearance({ page: 'sync' })"); pg.wait_for_timeout(800)
    sy = pg.evaluate("()=>{ const l=document.querySelector('#stage .sync-code-label'); return l ? { size: parseFloat(getComputedStyle(l).fontSize), color: getComputedStyle(l).color } : null; }")
    sh = hue(rgb(sy and sy["color"]))
    if not (sy and sy["size"] >= 18 and sh and 195 <= sh[0] <= 215): bad.append(("sync", sy, sh))
    pg.evaluate("()=>showAdvancedSettings()"); pg.wait_for_timeout(800)
    adv = pg.evaluate("()=>[...document.querySelectorAll('#stage .settings-textrow')].map(r=>parseFloat(getComputedStyle(r).fontSize))")
    if not adv or min(adv) < 18: bad.append(("advanced", adv))
    pg.evaluate("()=>showCredits()"); pg.wait_for_timeout(800)
    cr = pg.evaluate("""()=>[...document.querySelectorAll('#stage .credits-card > .credits-item')].map(r=>{ const l=r.querySelector('.settings-row-label') || r; return parseFloat(getComputedStyle(l).fontSize); })
      .concat([...document.querySelectorAll('#stage .credits-name')].map(n=>parseFloat(getComputedStyle(n).fontSize)))""")
    if not cr or min(cr) < 18: bad.append(("credits", sorted(set(cr))))
    for kind in ("legal", "terms", "privacy"):
        pg.evaluate("(k)=>showSettingsText(k)", kind); pg.wait_for_timeout(700)
        pr = pg.evaluate("()=>[...document.querySelectorAll('#stage .settings-prose > p')].map(p=>parseFloat(getComputedStyle(p).fontSize))")
        if not pr or min(pr) < 16: bad.append((kind, sorted(set(pr))))
    ck("(5) the pages Settings opens: switch rows, Account, the sync code, Advanced, Contributors and Legal/Terms/Privacy at the menu's size, hairlines between switch rows",
       not bad, bad[:4])
    ck("(4) no page errors", not errs, errs[:3])
    br.close()
print("\nALL PASS" if not fails else "\nFAILED: %d" % len(fails))
sys.exit(1 if fails else 0)
